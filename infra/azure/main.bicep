@description('Azure region for Hound Forward resources.')
param location string = resourceGroup().location

@description('Deployment environment name.')
param environmentName string = 'dev'

@description('Storage account name.')
param storageAccountName string

@description('Azure PostgreSQL server name.')
param postgresServerName string

@description('Azure Service Bus namespace name.')
param serviceBusNamespaceName string

@description('Container Apps environment name.')
param containerAppsEnvironmentName string

@description('API container app name.')
param apiAppName string = 'hound-api'

@description('Agent container app name.')
param agentAppName string = 'hound-agent'

@description('Worker job name.')
param workerJobName string = 'hound-worker'

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  name: '${storage.name}/default'
}

resource blobContainers 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = [for name in [
  'videos'
  'keypoints'
  'signals'
  'metrics'
  'reports'
  'logs'
]: {
  name: '${storage.name}/default/${name}'
  dependsOn: [blobService]
}]

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2023-12-01-preview' = {
  name: postgresServerName
  location: location
  sku: {
    name: 'Standard_B2s'
    tier: 'Burstable'
  }
  properties: {
    version: '16'
    authConfig: {
      activeDirectoryAuth: 'Enabled'
      passwordAuth: 'Enabled'
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    network: {
      publicNetworkAccess: 'Enabled'
    }
  }
}

resource serviceBus 'Microsoft.ServiceBus/namespaces@2024-01-01' = {
  name: serviceBusNamespaceName
  location: location
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
}

resource serviceBusQueue 'Microsoft.ServiceBus/namespaces/queues@2024-01-01' = {
  name: '${serviceBus.name}/runs'
  properties: {
    deadLetteringOnMessageExpiration: true
    maxDeliveryCount: 5
  }
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
  properties: {
    managedEnvironmentId: containerEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
      }
    }
    template: {
      containers: [
        {
          name: 'api'
          image: 'ghcr.io/example/hound-api:latest'
        }
      ]
    }
  }
}

resource agentApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: agentAppName
  location: location
  properties: {
    managedEnvironmentId: containerEnv.id
    template: {
      containers: [
        {
          name: 'agent'
          image: 'ghcr.io/example/hound-agent:latest'
        }
      ]
    }
  }
}

resource workerJob 'Microsoft.App/jobs@2024-03-01' = {
  name: workerJobName
  location: location
  properties: {
    environmentId: containerEnv.id
    configuration: {
      triggerType: 'Manual'
      replicaRetryLimit: 2
      replicaTimeout: 3600
    }
    template: {
      containers: [
        {
          name: 'worker'
          image: 'ghcr.io/example/hound-worker:latest'
        }
      ]
    }
  }
}

output storageAccountId string = storage.id
output postgresServerId string = postgres.id
output serviceBusNamespaceId string = serviceBus.id
output containerAppsEnvironmentId string = containerEnv.id
